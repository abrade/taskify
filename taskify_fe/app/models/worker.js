import DS from 'ember-data';
import { computed } from '@ember/object';

export default DS.Model.extend({
  name: DS.attr(),
  state: DS.attr(),

  stateLabelColor: computed('state', function() {
    let state = this.get('state')
    switch(state) {
      case 'OFFLINE': return "red"
      case 'ONLINE': return "green"
      default: return ""
    }
  }),
  stateColor: computed('state', function() {
    let state = this.get('state')
    switch(state) {
      case 'OFFLINE': return "negative"
      case 'ONLINE': return "positive"
      default: return ""
    }
  })
});
