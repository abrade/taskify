import Controller from '@ember/controller';
import { computed } from '@ember/object';

export default Controller.extend({
  queryParams: ['page', 'limit', 'state'],
  page: 1,
  limit: 20,
  next: computed(
    'model.meta.pagination.{self,next}.page',
    function() {
      const isNext = this.get('model.meta.pagination.self.page') != this.get('model.meta.pagination.next.page');
      return isNext;
    }
  ),
  prev: computed(
    'model.meta.pagination.{prev,self}.page',
    function() {
      const isPrev = this.get('model.meta.pagination.self.page') != this.get('model.meta.pagination.prev.page');
      return isPrev;
    }
  ),
  columns: computed(function() {
    return [
      {
        name: 'ID',
        column: 'id',
        hasLabel: true,
        columnLabel: 'taskColor'
      },
      {
        name: 'Title',
        column: 'title',
        hasLabel: false
      },
      {
        name: 'Script',
        column: 'script.name',
        hasLabel: false
      },
      {
        name: 'Worker',
        column: 'worker.name',
        hasLabel: false
      },
      {
        name: 'Scheduled',
        column: 'scheduled',
        hasLabel: false
      },
      {
        name: 'Run',
        column: 'run',
        hasLabel: false
      },
      {
        name: 'Team',
        column: 'script.team.name',
        hasLabel: false
      },
      {
        name: 'State',
        column: 'state',
        hasLabel: false
      },
    ]
  })
});
