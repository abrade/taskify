import DS from 'ember-data';
import { computed } from '@ember/object';

export default DS.Model.extend({
  name: DS.attr(),
  state: DS.attr(),
  stateColor: computed('state', function() {
    let state = this.get('state')
    switch(state) {
      case 'active': return "positive"
      case 'inactive': return "negative"
      default: return ""
    }
  }),
  icon: computed('state', function() {
    const state = this.get('state');
    switch(state) {
      case 'active': return "check_circle_outline"
      case 'inactive': return "error"
      default: return "help_outline"
    }
  }),
  active: computed('state', function() {
    return this.get('state') == 'active';
  })
});
