import Component from '@ember/component';
import { inject } from '@ember/service';

export default Component.extend({
  router: inject(),
  actions: {
    goToLink(item) {
      const redirectTo = this.get('redirectTo');
      const query_params = this.get('queryParams');
      let router = this.get('router');
      let params = {};
      params[query_params] = item.get('id');
      router.transitionTo(redirectTo, {queryParams: params});
    }
  }
});
