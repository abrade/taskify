import Controller from '@ember/controller';
import { inject as service } from '@ember/service';

export default Controller.extend({
  paperToaster: service(),  

  selected_type: "SCRIPT",
  team_id: "",
  script_name: "",
  cmd_name: "",
  opts: JSON.parse('[]'),
  actions: {
    submit() {
      let script = this.get('store').createRecord('script');
      const opts = this.get('opts');
      let options = {};
      let team_id = this.get('team_id').id;
      console.log("team_id", team_id, parseInt(team_id));
      opts.map(x => options[x.key] = x.value);
      script.set('name', this.get('script_name'));
      script.set('cmd', this.get('cmd_name'));
      script.set('team_id', parseInt(team_id));
      let toastService = this.get('paperToaster');
      //let opt = task.script.get('default_options');
      script.set('default_options', options);
//      task.script.default_options = JSON.parse(task.script.default_options + "");
      script.save().then(function() {
        toastService.show('Script saved', {
          duration: false,
          toastClass: 'md-warn',
          position: "top left"
        });
        //self.transitionTo('scripts');
      }).catch(function(reason) {
        console.error(reason);
        toastService.show('There was a failure while saving the script.', {
          duration: 10000,
          toastClass: "md-error",
          position: "top left"
        })
      });
    },
    addOption() {
      let opt = this.get('opts');
      opt.addObject({key: "", value: ""});
    },
    removeOption(index) {
      console.log(index);
      let opt = this.get('opts');
      opt.removeAt(index);
    }
  }
});
