describe ('Gopherairtime',function(){

    beforeEach(module('gopher'));

    describe('Recharge Dashboard',function(){

        var scope;
        var dataServiceController;
        beforeEach(inject(function($rootScope,$controller,$httpBackend){
            scope = $rootScope.$new();
            dataServiceController = $controller('dataService',{$scope:scope})
        }))

        it(' should fetch recharges with api call',inject(function($httpBackend){
                scope.fetchRecharges();
                var url = "/api/v1/recharges/";
                headers = {'Authorization' : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4'}
                $httpBackend
                    .expectGET(url)
                    .respond([
                            {
                                "url": "http://127.0.0.1:8000/api/v1/recharges/5/",
                                "id": 5,
                                "amount": "100.00",
                                "msisdn": "061973147",
                                "network_code": "TELKOM"
                            },
                            {
                                "url": "http://127.0.0.1:8000/api/v1/recharges/2/",
                                "id": 2,
                                "amount": "30.00",
                                "msisdn": "0634432512",
                                "network_code": "MTN"
                            }
                        ]);
                    $httpBackend.flush();
                expect(scope.fetchStatus).toBe(true);
                expect(scope.recharges.length).toBe(2);


        }))

        it(' should resubmit a recharge to api',inject(function($httpBackend){
            var data = {
                  id: 2,
                  msisdn: '0634432512',
                  amount: '30.00',
                  reference: '',
                  hotsocket_ref: 0,
                  status_message: '',
                  network_code : 'MTN'
            };
            scope.resubmit(data);
            $httpBackend.expectPATCH('/api/v1/recharges/2/').respond(null)
            $httpBackend.flush();
        }))

        it(' should send a delete request to the api',inject(function($httpBackend){
                var data = {
                            "id": 5,
                            "amount": "100.00",
                            "msisdn": "061973147",
                            "network_code": "TELKOM"
                            }
                scope.delete(data);
                $httpBackend.expectDELETE('/api/v1/recharges/5/').respond(null)
                $httpBackend.flush();
        }))


    })


})
