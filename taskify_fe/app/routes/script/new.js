import Route from '@ember/routing/route';
import { inject } from '@ember/service';

export default Route.extend({
  paperToaster: inject(),
  model() {
    return this.get('store').findAll('team');
  }
});
