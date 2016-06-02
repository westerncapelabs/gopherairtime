
       var app = angular.module('gopher', ['ngRoute','ngToast','ngAnimate','ngSanitize'])
                        .config(['$routeProvider',function($routeProvider){
                            $routeProvider.when('/',{
                                templateUrl:'/static/controlinterface/home.html',
                                controller:'dataService'
                            })
                        }]);
       app.controller('dataService',['$scope','$http','$location','$timeout','ngToast',function($scope,$http,$location,$timeout,ngToast){
                    console.log('ssssss')
                    $scope.recharges = {};
                    $scope.fetchStatus;
                    $scope.searchtext;
                    $scope.showReturnButton=false;
                    ngToast.create('Gopherairtime.')
                    $scope.fetchRecharges = function (){

                      $http({ method:'GET',
                             url:'/api/v1/recharges/',
                             headers : { "Authorization" : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4' }
                      })
                      .success(function(data){
                         $scope.recharges = data;
                         $scope.fetchStatus=true;
                         console.log($scope.recharges)


                      })
                      .error(function(){
                         $scope.fetchStatus=false;
                      })
                    }
                    $scope.delete = function (recharge){
                      $http({ method:'DELETE',
                             data:{id:recharge.id},
                             url:'/api/v1/recharges/'+recharge.id+'/' ,
                             headers : { "Authorization" : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4' }
                      })
                      .success(function(data){
                           $scope.reloadTable();
                           ngToast.create({
                            className: 'success',
                            content: "<p class='flow-text'>Success !</p>"
                          });

                      })
                      .error(function(){
                        ngToast.create({
                          className: 'warning',
                          content: "<p class='flow-text'>Failure !</p>"
                        });
                      })
                    }
                    $scope.resubmit = function (recharge){
                      $http({ method:'PATCH',
                             data:{
                                id:recharge.id,
                                msisdn:recharge.msisdn,
                                amount:recharge.amount,
                                reference:'',
                                hotsocket_ref:0,
                                status_message:'',
                                network_code :recharge.network_code

                              },
                             url:'/api/v1/recharges/'+recharge.id+'/',
                             headers : { "Authorization" : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4' }
                      })
                      .success(function(data){
                         $scope.reloadTable();
                         ngToast.create({
                          className: 'success',
                          content: "<p class='flow-text'>Success !</p>"
                        });

                      })
                      .error(function(){
                          ngToast.create({
                          className: 'warning',
                          content: "<p class='flow-text'>Failiure !</p>"
                        });
                      })
                    }

                    $scope.search = function(query){
                      $scope.searchResults=[];
                      if($scope.fetchStatus){
                          if($scope.searchtext==''){
                              $scope.reloadTable();
                          }
                          $scope.recharges.forEach(function(recharge){
                            var contains;
                            for(option in recharge){
                              var value = recharge[option]
                              if(option == '$$hashKey' || option == 'url'){
                                continue
                              }
                              else if(isNaN(value)){
                                contains = value.toLowerCase().indexOf(query.toLowerCase()) != -1;
                                if(contains){
                                  break;
                                }
                              }
                              else{
                                if(value!=null){
                                  contains = value.toString().toLowerCase().indexOf(query.toLowerCase()) != -1;
                                  if(contains){
                                    break;
                                  }
                                }
                              }

                            }
                            if(contains){
                              $scope.searchResults.push(recharge)
                            }
                          })
                      }
                      $scope.recharges=$scope.searchResults;
                      $scope.showReturnButton=true;
                      $scope.searchResults=[];


                    }

                    $scope.reloadTable = function(){
                      $scope.fetchRecharges();
                      $scope.showReturnButton=false;


                    }


               }])
