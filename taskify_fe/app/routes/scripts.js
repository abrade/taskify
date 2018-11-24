import Route from '@ember/routing/route';
import DataTableRouteMixin from 'ember-data-table/mixins/route';

export default Route.extend(DataTableRouteMixin, {
  modelName: "script",
  actions: {
    onClick(row) {
      let router = this.get('router');
      // router.transitionTo("task", {queryParams: {task: row.id} });
    },
    addScript(row) {
      let router = this.get('router');
      router.transitionTo("script.new");    
    }
  }
});
