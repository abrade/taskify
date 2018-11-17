import Route from '@ember/routing/route';
import RSVP from 'rsvp';

export default Route.extend({
  actions: {
    willTransition(transition) {
      let task = this.modelFor(this.routeName);
      if (task.script.id == undefined &&
          !confirm('Are you sure you want to abandon progress?')) {
        transition.abort();
      } else {
        // Bubble the `willTransition` action so that
        // parent routes can decide whether or not to abort.
        task.script.deleteRecord();
        return true;
      }
    },
    selectTeam(event) {
      const team_id = parseInt(event.target.value);
      let task = this.modelFor(this.routeName);
      this.get('store')
         .findRecord('team', team_id).then(function(team) {
            task.script.set('team_id', team_id);
//            task.script.set('team', team);
    
         });
    },
    submit() {
      let task = this.modelFor(this.routeName);
      var self = this;
      let opt = task.script.get('default_options');
      task.script.set('default_options', JSON.parse(opt + ""));
//      task.script.default_options = JSON.parse(task.script.default_options + "");
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
