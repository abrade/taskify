import Route from '@ember/routing/route';
import RSVP from 'rsvp';

export default Route.extend({
  model() {
    return RSVP.hash(
      {
        workers: this.get('store').findAll('worker'),
        queues: this.get('store').findAll('workerqueue')
      }
    )
  }
});
