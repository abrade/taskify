import DS from 'ember-data';

export default DS.Model.extend({
  name: DS.attr(),
  cmd: DS.attr(),
  status: DS.attr({ defaultValue: "ACTIVE" }),
  team: DS.belongsTo('team'),
  team_id: DS.attr(),
  type: DS.attr({ defaultValue: "SCRIPT"}),
  default_options: DS.attr(),
});
