module.exports = function(config){
  config.set({

    basePath : './',

    files: [

      'controlinterface/static/controlinterface/js/angular/angular.js',
      'controlinterface/static/controlinterface/js/angular-mocks/angular-mocks.js',
      'controlinterface/static/controlinterface/js/gopher.js',
      'controlinterface/static/controlinterface/js/angular-animate/angular-animate.js',
      'controlinterface/static/controlinterface/js/angular-sanitize/angular-sanitize.min.js',
      'controlinterface/static/controlinterface/js/angular-route/angular-route.js',
      'controlinterface/static/controlinterface/js/ngToast-master/dist/ngToast.js',
      'test/*.js'
    ],

    autoWatch : true,

    frameworks: ['jasmine'],

    browsers : ['Chrome', 'Firefox'],

    plugins : [
            'karma-chrome-launcher',
            'karma-jasmine'
            ],

    junitReporter : {
      outputFile: 'test_out/unit.xml',
      suite: 'unit'
    }

  });
};
