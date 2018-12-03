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
      var self = this;
      let script = this.get('store').createRecord('script');
      let options = this.get('opts');
      console.log("options ", options);
      script.set('name', this.get('script_name'));
      script.set('cmd', this.get('cmd_name'));
      script.set('team_id', this.get('team_id'));
      console.log('script', script);
      let toastService = this.get('paperToaster');
      console.log(toastService);
      this.get('paperToaster').show('Create', {
        duration: false,
        toastClass: 'md-warn',
        position: "top left"
      });
      //let opt = task.script.get('default_options');
      //task.script.set('default_options', JSON.parse(opt + ""));
//      task.script.default_options = JSON.parse(task.script.default_options + "");
      //task.script.save().then(function() {
      //  self.transitionTo('scripts');
      //}).catch(function(reason) {
      //});
    },
    addOption() {
      let opt = this.get('opts');
      opt.addObject({key: "", value: ""});
    }
  }
});
