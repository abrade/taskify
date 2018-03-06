import DS from 'ember-data';

export default DS.Model.extend({
  concurrency: DS.attr(),
  prefetchcount: DS.attr(),
  statistics: DS.attr()
});
