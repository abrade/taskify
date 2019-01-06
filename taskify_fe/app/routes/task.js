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
      { name: "Queue", key: "worker.name" },
      { name: "Script", key: "script.name"},
      { name: "Command", key: "script.cmd"}
    ]
    return RSVP.hash(
      {
        task: this.get('store').findRecord('task', params.task),
        details: details
      }
    )
  }
});
