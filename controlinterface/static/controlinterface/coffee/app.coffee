
app = angular.module 'gopherCoffee' , []

app.controller('gopherControl' , ['$scope','$http',($scope,$http) ->
    console.log "INITIATING GOPHER CONTROL"

    $scope.greeting = 'Gopher airtime : Recharges'
    $scope.recharges
    $scope.searchResults = []
    $scope.fetchStatus=false
    $scope.newRecharge=false;
    $scope.new_msisdn
    $scope.new_amount
    $scope.new_network
    $scope.shownewbtn=true
    $scope.error=false
    $scope.searchtext

    #


    # Fetch recharges from api
    $scope.fetchRecharges = () ->
        console.log 'fetching recharges'
        config =
            method : "GET"
            url : "/api/v1/recharges/"
            headers : Authorization : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4'
        $http(config)
             .success (data) ->
                $scope.recharges = data
                console.log "feteched"
                console.log $scope.recharges
                $scope.fetchStatus=true
             .error () ->
                alert "Error failure!"

    # Resubmitting a recharge to the api
    $scope.resubmitRecharge = (recharge) ->
        console.log 'resubmit recharge'
        config =
            method:'PATCH'
            data:
                id:recharge.id
                msisdn:recharge.msisdn
                amount:recharge.amount
                reference:''
                hotsocket_ref:0
                status_message:''
                network_code :recharge.network_code
            url:'/api/v1/recharges/'+recharge.id+'/'
            headers :
                Authorization : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4'

        $http(config)
             .success (data) ->
                $scope.recharges = data
                $scope.fetchRecharges()
                console.log "Success !"
             .error() ->
                alert "Error failure!"

    # Delete a recharge from the api
    $scope.deleteRecharge = (recharge) ->
        console.log 'deleting recharges'
        config =
            method:'DELETE'
            data:
                id:recharge.id
            url:'/api/v1/recharges/'+recharge.id+'/'
            headers :
                Authorization : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4'

        $http(config)
             .success (data) ->
                $scope.recharges = data
                $scope.fetchRecharges()
                console.log "Success !"
             .error() ->
                alert "Error failure!"

    # Adding details of a new recharge
    $scope.submitNew = () ->
        data =
            msisdn : $scope.new_msisdn
            amount: $scope.new_amount
            network_code : $scope.new_network
        config =
            method:'POST'
            data: data
            url:'/api/v1/recharges/'
            headers :
                Authorization : 'Token bd2b2e23762b43b8f86ed4e4d1137d87000a5fc4'
        console.log config
        $http(config)
             .success (data) ->
                $scope.fetchRecharges()
                $scope.newRecharge=!$scope.newRecharge
             .error (err) ->
                $scope.error = err;
                console.log(err)

    # Seacrhing for a recharge from the list
    $scope.search = (query) ->
        $scope.searchResults = []
        if $scope.fetchStatus
            if $scope.searchtext == ''
                $scope.refresh()
            $scope.recharges.forEach (recharge) ->
                contains = null
                for option of recharge
                    value = recharge[option]
                    if option == '$$hashKey' || option == 'url'
                        continue
                    else if isNaN(value)
                        contains = value.toLowerCase().indexOf(query.toLowerCase()) != -1;
                        if contains
                          break
                    else
                        if value!=null
                            contains = value.toString().toLowerCase().indexOf(query.toLowerCase()) != -1;
                            if contains
                                break
                if contains
                        $scope.searchResults.push(recharge)
        $scope.recharges=$scope.searchResults
        $scope.searchResults=[]

    $scope.refresh = () ->
        $scope.fetchRecharges()


])
