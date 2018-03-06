import Route from '@ember/routing/route';
import RSVP from 'rsvp';

export default Route.extend({
  queryParams: {
    task: { refreshModel: true }
  },
  model(params) {
    let details = [
      { name: "Scheduled", key: "scheduled" },
      { name: "Run", key: "run" },
      { name: "Scheduled by", key: "scheduledBy" },
      { name: "Locks", key: "locks" },
    ]
    return RSVP.hash(
      {
        task: this.get('store').findRecord('task', params.task),
        logs: this.get('store').query('tasklog', params),
        details: details
      }
    )
  }
});
