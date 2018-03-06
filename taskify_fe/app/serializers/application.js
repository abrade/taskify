import DS from 'ember-data';

export default DS.JSONAPISerializer.extend({
  keyForAttribute: function(key) {
    return key;
  },

  keyForRelationship: function(key) {
    return key;
  }
});
