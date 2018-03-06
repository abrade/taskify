import Route from '@ember/routing/route';
import RSVP from 'rsvp';

export default Route.extend({
  actions: {
    submit() {
      let task = this.modelFor(this.routeName);
      var self = this;
//      task.script.team_id = task.script.team.id;
      console.log(task.script);
      console.log(task.script.team_id);
      task.script.save().then(function() {
        self.transitionTo('scripts');
      }).catch(function(reason) {
      });
    }
  },
  model() {
    return RSVP.hash(
      {
        script: this.get('store').createRecord('script'),
        teams: this.get('store').findAll('team')
      }
    )
  }
});
