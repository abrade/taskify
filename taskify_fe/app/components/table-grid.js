import Component from '@ember/component';

export default Component.extend({
  actions: {
    goToLink(item) {
      console.log(item);
    }
  }
});
