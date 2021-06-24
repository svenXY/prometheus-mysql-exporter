import time
import logging

from croniter import croniter
from datetime import datetime, timezone

log = logging.getLogger(__name__)


def schedule_job(scheduler, interval, cron, cron_tz, func, *args, **kwargs):
    """
    Schedule a function to be run at a fixed interval, or based on a
    cron expression. Uses the croniter module for cron handling.

    Works with schedulers from the stdlib sched module.
    """

    def scheduled_run(scheduled_time, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception:
            log.exception('Error while running scheduled job.')

        current_time = time.monotonic()
        if cron:
            delay = calc_cron_delay(cron, cron_tz)
            # Assume the current_dt used by calc_cron_delay() represents the
            # same instant as current_time. Should be approximately true.
            next_scheduled_time = current_time + delay
            log.debug('Next cron based run in %(delay_s).2fs.',
                      {'delay_s': delay})
        else:
            next_scheduled_time = scheduled_time + interval
            while next_scheduled_time < current_time:
                next_scheduled_time += interval
            log.debug('Next interval based run in %(delay_s).2fs.',
                      {'delay_s': next_scheduled_time - current_time})

        scheduler.enterabs(time=next_scheduled_time,
                           priority=1,
                           action=scheduled_run,
                           argument=(next_scheduled_time, *args),
                           kwargs=kwargs)

    next_scheduled_time = time.monotonic()
    scheduler.enterabs(time=next_scheduled_time,
                       priority=1,
                       action=scheduled_run,
                       argument=(next_scheduled_time, *args),
                       kwargs=kwargs)


def calc_cron_delay(cron, cron_tz):
    """
    Return seconds until the next cron run time by parsing a cron
    expression. Uses the croniter module for cron handling.
    """

    current_dt = datetime.now(timezone.utc)
    if cron_tz:
        current_dt = current_dt.astimezone(cron_tz)

    next_dt = croniter(cron, current_dt).get_next(datetime)

    delay = (next_dt - current_dt).total_seconds()
    assert delay > 0, 'Cron delay should be positive.'

    return delay
