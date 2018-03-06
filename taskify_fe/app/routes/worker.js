import Route from '@ember/routing/route';
import RSVP from 'rsvp';

export default Route.extend({
  queryParams: {
    worker: { refreshModel: true }
  },
  model(params) {
    return RSVP.hash(
      {
        worker: this.get('store').findRecord('worker', params.worker),
        queues: this.get('store').query('workerqueue', {worker_id: params.worker}),
        options: this.get('store').queryRecord('workeroption', {worker_id: params.worker})
      }
    )
  }
});
