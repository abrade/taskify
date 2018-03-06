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
      case 'FAILED':
      case 'RETRIED':
      case 'FAILED-ACKED': return "negative"
      case 'SUCCEED': return "positive"
      case 'STARTED':
      case 'PRERUN':
      default: return ""
    }
  })
});
