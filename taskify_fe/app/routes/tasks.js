import Route from '@ember/routing/route';
import DataTableRouteMixin from 'ember-data-table/mixins/route';

export default Route.extend(DataTableRouteMixin, {
  modelName: 'task',
  queryParams: {
    filter: { refreshModel: true },
    page: { refreshModel: true },
    size: { refreshModel: true },
    sort: { refreshModel: true },
    state: { refreshModel: true },
    limit: { refreshModel: true }
  },
  mergeQueryOptions(params) {
    return {
        'state': params.state,
        'filter[worker': params.worker,
        'filter[team]': params.team
    };
  }
/*   queryParams: {
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
    return this.get('store').query('task', params);
  } */
});
