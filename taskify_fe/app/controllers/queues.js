import Controller from '@ember/controller';

export default Controller.extend({
  selected_row: null,
  status_text: 'deactivate',
  showPrompt: false,
  showAdd: false,
  actions: {
    addQueue(ok, name) {
      console.log(ok, name)
    },
    onAddQueue() {
      this.toggleProperty('showAdd');
    },
    onClick(row) {
      console.log(row, arguments);
      console.log(row.get('state'));
      if (row.get('state') == 'active') {
        this.set('status_text', 'deactivate');
      }
      else {
        this.set('status_text', 'activate');
      }
      this.set('selected_row', row);
      this.toggleProperty('showPrompt');
    },
    closeDialog(change_status) {
      let row = this.get('selected_row')
      this.set('showPrompt', false);
      this.set('selected_row', null);
      if(!change_status) {
        return;
      }
      const activate = this.get('status_text') == 'activate'
      if (activate) {
        row.set('state', 'active');
      }
      else {
        row.set('state', 'inactive');
      }
      console.log(row, activate);

      row.save()
      
    }
  }
});
