import DS from 'ember-data';
import { computed } from '@ember/object';

export default DS.Model.extend({
  taskId: DS.attr(),
  run: DS.attr(),
  worker: DS.belongsTo('worker'),
  state: DS.attr(),
  
  taskColor: computed('state', function() {
    let state = this.get('state')
    switch(state) {
      case 'RETRIED':
      case 'FAILED': return "red"
      case 'FAILED-ACKED': return "orange"
      case 'STARTED': return "olive"
      case 'PRERUN': return "teal"
      case 'SUCCEED': return "green"
      default: return "gray"
    }
  })
});
