import DS from 'ember-data';
import { computed } from '@ember/object';

export default DS.Model.extend({
  name: DS.attr(),
  cmd: DS.attr(),
  status: DS.attr({ defaultValue: "ACTIVE" }),
  team: DS.belongsTo('team'),
  team_id: DS.attr(),
  type: DS.attr({ defaultValue: "SCRIPT"}),
  default_options: DS.attr(),

  icon: computed('state', function() {
    const state = this.get('status');
    switch(state) {
      case 'ACTIVE': return "check_circle_outline"
      case 'UNACTIVE': return "error"
      default: return "help_outline"
    }
  })
});
