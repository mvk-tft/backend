import networkx as nx
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from api.models import Shipment
from matching.models import Match
from matching.task_helpers import validate_times, validate_capacities, get_time_estimations, calculate_travel_times, \
    split_shipments

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def matching_task():
    # Only retrieve shipments not yet matched
    outer_query = Q(match_outer=None) | Q(match_outer__status=Match.Status.REJECTED)
    inner_query = Q(match_inner=None) | Q(match_inner__status=Match.Status.REJECTED)

    shipments = Shipment.objects.filter(outer_query, inner_query).select_related('origin',
                                                                                 'destination') \
        .prefetch_related('cargo_set').annotate(cargo_weight=Coalesce(Sum('cargo__weight'), 0)).annotate(
        cargo_volume=Coalesce(Sum('cargo__volume'), 0))
    matches, estimated_times = find_matches(split_shipments(shipments))
    prepared = []
    for (f, s) in matches:
        # Outer shipment is the one going the whole route and whose truck will be used
        times = estimated_times[(f, s)]
        match = Match(outer_shipment=shipments.get(pk=f), inner_shipment=shipments.get(pk=-s),
                      start_time=times['outer_start_time'],
                      estimated_inner_start_time=times['inner_start_time'],
                      estimated_inner_arrival_time=times['inner_arrival_time'],
                      estimated_outer_arrival_time=times['outer_arrival_time'])
        prepared.append(match)
    logger.info(f'Matches created: {len(prepared)}')
    Match.objects.bulk_create(prepared)


def find_matches(nearby_shipments):
    graph = nx.Graph()
    results = []
    estimated_times = {}
    for key, value in nearby_shipments.items():
        graph.clear()
        count = len(value)

        if count <= 1:
            continue

        # Travel time between the two origins, last origin and first arrival and the two destinations, respectively
        src_src_time, src_dst_time, dst_dst_time = calculate_travel_times(value)
        max_time = max(map(max, src_src_time)) + max(src_dst_time) + max(map(max, dst_dst_time))

        for i in range(count):
            f = value[i]
            if not f.truck:
                continue
            for j in range(count):
                if i == j:
                    continue

                s = value[j]
                src_travel_time = src_src_time[i][j]
                dst_travel_time = dst_dst_time[j][i]
                travel_time = src_dst_time[j]

                if validate_times(f, s, travel_time, src_travel_time, dst_travel_time) and validate_capacities(f, s):
                    driver_st, other_st, other_at, driver_at = get_time_estimations(f, s, travel_time,
                                                                                    src_travel_time,
                                                                                    dst_travel_time)
                    estimated_times[(f.pk, -s.pk)] = {
                        'outer_start_time': driver_st,
                        'inner_start_time': other_st,
                        'inner_arrival_time': other_at,
                        'outer_arrival_time': driver_at,
                    }

                    total_time = src_travel_time + travel_time + dst_travel_time

                    graph.add_edge(f.pk, -s.pk, weight=max_time - total_time)
        results += [(f, s) if f >= 0 else (s, f) for (f, s) in nx.max_weight_matching(graph, maxcardinality=True)]
    return results, estimated_times
