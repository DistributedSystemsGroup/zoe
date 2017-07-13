/**
 * Created by venzano on 13/07/2017.
 */

function get_executions() {
    
}

var data = get_executions();
var viewModel = ko.mapping.fromJS(data);

function updateViewModel()
{
    var data = get_executions();
    ko.mapping.fromJS(data, viewModel);
}

var exec_update_interval = setInterval(updateViewModel, 5000);
