describe ('Gopherairtime',function(){

    beforeEach(module('gopher'));

    describe('Recharges',function(){

        var scope;
        var dataServiceController;
        beforeEach(inject(function($rootScope,$controller,$httpBackend){
            scope = $rootScope.$new();
            dataServiceController = $controller('dataService',{$scope:scope})
        }))

        it('should fetch recharges with api call',function(){

                scope.fetchRecharges();
                expect(scope.fetchStatus.toBe(true));
                expect(scope.recharges.length.toBe(10));


        })
        it('should fetch recharges from api',function(){

            var url = 'api/v1/recharges/';
            $httpBackend.expect('GET', url,function (headers) {
                return !headers['Au']; // checking for this header's presence
            })
            .respond();
        })
        it('should delete a recharge from api',function(){
            var response = $httpBackend.expect('api/v1/recharges/')
                                       .respond(null);
        })
        it('should resubmit a recharge to api',function(){
            var response = $httpBackend.expect('api/v1/recharges/')
                                       .respond(null);
        })
    })


})
