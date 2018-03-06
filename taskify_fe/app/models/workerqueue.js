import DS from 'ember-data';
import { computed } from '@ember/object';

export default DS.Model.extend({
  name: DS.attr(),
  state: DS.attr(),
  stateColor: computed('state', function() {
    let state = this.get('state')
    switch(state) {
      case 'active': return "positive"
      case '': return "negative"
      default: return ""
    }
  })
});
