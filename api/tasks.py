from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from api.models import Shipment

logger = get_task_logger(__name__)


@periodic_task(run_every=(crontab(minute='*/1')), name='matching_task', ignore_result=True)
def test():
    shipments = Shipment.objects.all()
    for shipment in shipments:
        logger.info(str(shipment))
