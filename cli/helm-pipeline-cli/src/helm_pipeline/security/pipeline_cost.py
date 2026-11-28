"""Estimate the runner cost of a whole pipeline run from the timings of its jobs."""

from datetime import datetime

from helm_pipeline.security.cost_estimate import CostEstimate




class PipelineCost:
    """Add one total runner cost estimate for the finished jobs of a pipeline run to the job summary."""

    def __init__(self, github, estimate=None):
        """Store the GitHub file writer and the cost estimate.

        Args:
            github: A GitHubFiles instance.
            estimate: A CostEstimate instance; defaults to the standard runner price.
        """
        self.github = github
        self.estimate = estimate if estimate is not None else CostEstimate()

    def write(self, jobs):
        """Add the total billed minutes and estimated cost of the finished jobs to the job summary.

        Args:
            jobs: Job dictionaries from gh run view --json jobs, with startedAt, completedAt and conclusion.
        """
        finished = [job for job in jobs if self.is_finished(job)]
        minutes = sum(self.estimate.billed_minutes(self.duration(job)) for job in finished)
        rows = [
            ('Jobs billed', str(len(finished))),
            ('Billed minutes', str(minutes)),
            ('Estimated cost', f'USD {self.estimate.cost(minutes):.4f}'),
            ('Scope', 'all finished jobs of this run; each job rounded up to whole minutes'),
        ]
        self.github.append_table('Pipeline cost estimate', ['Item', 'Value'], rows)

    def is_finished(self, job):
        """Return True when a job has run to completion and is billed; skipped and running jobs are not."""
        completed = job.get('completedAt') or ''
        return bool(job.get('conclusion')) and job.get('conclusion') != 'skipped' and not completed.startswith('0001')

    def duration(self, job):
        """Return the duration of a job in seconds."""
        started = datetime.fromisoformat(job['startedAt'].replace('Z', '+00:00'))
        completed = datetime.fromisoformat(job['completedAt'].replace('Z', '+00:00'))
        return (completed - started).total_seconds()
