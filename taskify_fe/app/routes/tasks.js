import Route from '@ember/routing/route';
import { computed } from '@ember/object';
import RSVP from 'rsvp';

export default Route.extend({
  queryParams: {
    state: { refreshModel: true },
    page: { refreshModel: true },
    limit: { refreshModel: true },
    script: { refreshModel: true },
    worker: { refreshModel: true },
    team: { refreshModel: true },
  },
  model(params) {
    params.page = params.page || 1;
    params.limit = params.limit || 20;
    console.log(params);
    return this.get('store').query('task', params);
  }
});
