import DS from 'ember-data';
import { computed } from '@ember/object';

export default DS.Model.extend({
  title: DS.attr(),
  scheduled: DS.attr(),
  run: DS.attr(),
  state: DS.attr(),
  locks: DS.attr(),
  options: DS.attr(),
  scheduledBy: DS.attr(),
  worker: DS.belongsTo('workerqueue'),
  depends: DS.attr(),
  children: DS.hasMany('task', {inverse: null}),
  parent: DS.belongsTo('task', {inverse: null}),
  script: DS.belongsTo('script'),
  logs: DS.belongsTo('tasklog'),

  taskColor: computed('state', function() {
    let state = this.get('state')
    switch(state) {
      case 'FAILED': return "red"
      case 'FAILED-ACKED': return "orange"
      case 'STARTED': return "olive"
      case 'PRERUN': return "teal"
      case 'SUCCEED': return "green"
      default: return "gray"
    }
  })
});
