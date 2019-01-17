import EmberRouter from '@ember/routing/router';
import config from './config/environment';
import RouterScroll from 'ember-router-scroll';

const Router = EmberRouter.extend(RouterScroll, {
  location: config.locationType,
  rootURL: config.rootURL
});

Router.map(function() {
  this.route('tasks');
  this.route('task');
  this.route('workers');
  this.route('worker');
  this.route('scripts');

  this.route('script', function() {
    this.route('new');
  });
  this.route('queues');
  this.route('dashboard');
});

export default Router;
