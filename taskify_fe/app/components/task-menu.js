import Component from '@ember/component';
import { computed } from '@ember/object';
import { inject } from '@ember/service';
import { run } from '@ember/runloop';
import $ from 'jquery';

export default Component.extend({
  store: inject(),
  router: inject(),
  task: null,
  leftSideBarOpen: true,
  leftSideBarLockedOpen: true,
  menu: computed('params.[]', function () {
    let states = this.get('states')
    if (states == undefined) {
      states = {
        "STARTED": 0,
        "ALL": 0,
        "FAILED": 0,
        "FAILED-ACKED": 0,
      }
    }
    return [
      {name: "ALL", color: "teal", label: "All", count: states.ALL},
      {name: "STARTED", color: "olive", label: "Running", count: states.STARTED},
      {name: "FAILED", color: "red", label: "Failed", count: states.FAILED},
      {name: "FAILED-ACKED", color: "orange", label: "Acked", count: states["FAILED-ACKED"]},
    ]
  }),
  actions: {
    onScript() {
      let router = this.get('router');
      router.transitionTo("scripts");
    },
    onWorker() {
      let router = this.get('router');
      router.transitionTo("workers");
    },
    onQueue() {
      let router = this.get('router');
      router.transitionTo('queues');
    }
  },
  didReceiveAttrs() {
    this._super(...arguments);
    $.getJSON('/tasks/state').then(data => {
      run(() => {
        this.set('states', data.data.attributes);
      });
    });
  }
});
