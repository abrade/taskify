import Route from '@ember/routing/route';
import RSVP from 'rsvp';
import { inject } from '@ember/service';

export default Route.extend({
  paperToaster: inject(),
  model() {
    return RSVP.hash(
      {
        types: ['SCRIPT', 'FUNCTION'],
        teams: this.get('store').findAll('team')
      }
    )
  }
});
