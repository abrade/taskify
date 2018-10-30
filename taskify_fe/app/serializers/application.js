import DS from 'ember-data';

export default DS.JSONAPISerializer.extend({
  keyForAttribute: function(key) {
    return key;
  },

  keyForRelationship: function(key) {
    return key;
  },

  normalizeQueryResponse(store, clazz, payload) {
    const result = this._super(...arguments);
    result.meta = result.meta || {};

    if (payload.links) {
      result.meta.pagination = this.createPageMeta(payload.links);
    }

    return result;
  },

  createPageMeta(data) {

    let meta = {};

    Object.keys(data).forEach(type => {
      const link = data[type];
      meta[type] = {};
      let a = document.createElement('a');
      a.href = link;
      a.search.slice(1).split('&').forEach(pairs => {
        const [param, value] = pairs.split('=');
        if (param == 'page') {
          meta[type].page = parseInt(value);
        }
        if (param == 'limit') {
          meta[type].limit = parseInt(value);
        }

      });
      a = null;
    });

    return meta;

  }

});
