import Route from '@ember/routing/route';

export default Route.extend({
  queryParams: {
    state: { refreshModel: true },
    page: { refreshModel: true },
    max_entries: { refreshModel: true },
    script: { refreshModel: true },
    worker: { refreshModel: true },
    team: { refreshModel: true },
  },
  page: 1,
  max_entries: 20,
  model(params) {
    params.page = params.page || 1;
    params.max_entries = params.max_entries || 20;
    return this.get('store').query('task', params);
  }
});
