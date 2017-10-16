/**
 * Websocket client
 */

var currentPath = '';

ws.onopen = function()
{
    actionChangeDir({'path': '', 'name': ''});
};

ws.onmessage = function(evt)
{
    var data = JSON.parse(evt.data);

    if (data.action == 'chdir')
    {
        responseChangeDir(data.response);
    }
    else if (data.action == 'list_dir')
    {
        responseShowFiles(data.response);
    }
    else if (data.action == 'create_dir')
    {
        responseCreateDir(data.response);
    }
    else if (data.action == 'update_buffer')
    {
        responsePutToBuffer(data.response);
    }
    else if (data.action == 'paste_files')
    {
        responsePasteFiles(data.response);
    }
    else if (data.action == 'remove_files')
    {
        responseRemoveFiles(data.response);
    }
    $('#dialog_wait').dialog('close');
};

function actionChangeDir(data)
{
    sendRequest('chdir', {'path': data.path, 'name': data.name});
}

function actionRemoveFiles()
{
    actionPutToBuffer('remove');
    sendRequest('remove_files');
}

function actionUploadFile()
{
    var uploadWindow = window.open('/upload', 'Upload', "width=500, height=100, location=no, menubar=no, " +
    "scrollbars=no, status=no, toolbar=no");
}

function actionPutToBuffer(action)
{
    var files = [];
    $('#files').each(function(){
        var current = $(this);
        current.find('li').each(function(key, li) {
            if ($(li).hasClass('selected')) {
                files.push($(li).data('name'));
            }
        }
        );
    }
    );
    var data = {'files': files, 'action': action}
    sendRequest('update_buffer', data);
}

function actionApplyOrder(order)
{
    var files = $('#files');
    var file_data = files.children('li').get();
    file_data.sort(function(a, b) {
        if (order == 'name') {
            //var sort = $(a).text().toUpperCase().localeCompare($(b).text().toUpperCase());
            var sort = $(a).data('name').toString().toUpperCase().localeCompare($(b).data('name').toString().toUpperCase());
        } else if (order == 'size') {
            var sort = $(a).data('size') < $(b).data('size');
        }
        return sort;
    });
    $.each(file_data, function(idx, itm) {
        files.append(itm);
    });

}

function actionFormatFileSize(value)
{
    if (value == 0) {
        return "0.0 b";
    }
    var p = Math.floor(Math.log(value) / Math.log(1024));
    return (value / Math.pow(1024, p)).toFixed(1) + ' '+' KMGTP'.charAt(p) + 'b';
}

function actionShowProperties()
{
    var total_size = 0;
    var names = [];
    var owners = [];
    var total_files = $('.selected').length;
    if (total_files > 1) {
        $('#files').each(function () {
            var current = $(this);
            current.find('li').each(function (key, li) {
                if ($(li).hasClass('selected')) {
                    names.push($(li).data('name'));
                    total_size += $(li).data('size');
                    owners.push($(li).data('owner'));
                }
            }
            );
        }
        );
        var is_only = owners.every(function(owner) {
            return owner === owners[0];
        });
        $('#property_file_name').text(names.slice(0,3).join(', ') + (total_files > 3 ? ', ... (' + total_files + ')': ''));
        $('#property_file_size').text(actionFormatFileSize(total_size) + ' (' + total_size + ' bytes)');
        $('#property_file_owner').text(is_only ? owners[0]: '...');
        $('#property_file_mode').text('???');
    } else {
        var file = $('.selected');
        $('#property_file_name').text(file.data('name'));
        $('#property_file_size').text(actionFormatFileSize(file.data('size')) + ' (' + file.data('size') + ' bytes)');
        $('#property_file_owner').text(file.data('owner'));
        $('#property_file_mode').text(file.data('mode'));
    }

    $("#dialog_properties").dialog('open');


}

function responseShowFileInfo(file)
{
    $('#info_file_name').text(file.name);
    $('#info_file_size').text(actionFormatFileSize(file.size));
    $('#info_file_mime').text(file.mime);
}

function responseShowFiles(data)
{
    $('.message').text('');
    $('#files').empty();

    if (data.dir != '/'){
        $('#files').append('<li id="parent" data-name=".."><img src="/static/filemanager/img/mime/inode-directory.png">..</li>');
        $('#parent').dblclick(function() {
            actionChangeDir({'path': '', 'name': '..'});
        });
    }

    if (data.error) {
        $('.message').text(data.error);
        return
    }

    if (data.files) {

        $.each(data.files, function (num, file) {
            $('#files').append('<li data-name="'+ file.name + '" data-type="'+ file.type +'" data-size="'+ file.size +

                '"data-mode="' + file.mode + '" data-owner="' + file.owner_name +'" id="file_' + num + '"> ' +

                '<img src="/static/filemanager/img/mime/' + file.type + '.png" />' + file.name +

                '<span style="float: right">' + actionFormatFileSize(file.size) +'</span></li>');

            $('#file_' + num).click(function (e) {
                if (e.ctrlKey) {
                    $('#file_' + num).toggleClass('selected');
                } else {
                    $('#files').each(function(){
                        var current = $(this);
                        current.find('li').each(function(key, li) {
                                if ($(li).hasClass('selected')) {
                                    $(li).toggleClass('selected');
                                }
                            }
                        )
                        }
                    );
                    $('#file_' + num).toggleClass('selected');
                    responseShowFileInfo(file);
                }
            });

            $('#file_' + num).dblclick(function () {
                if (file.type == 'inode-directory') {
                    actionChangeDir({'path': file.path, 'name': file.name})
                } else if (file.real_type == 'inode-directory') {
                    actionChangeDir({'path': file.real_path, 'name': ''})
                } else {
                    window.open('/download' + file.path + '/' +file.name, 'Download', "width=10, height=10, location=no, menubar=no, " +
    "scrollbars=no, status=no, toolbar=no");
                }
            });
        });
        actionApplyOrder('name');
    } else {
        $('.message').text('Empty directory');
    }
}

function responseCreateDir(data)
{
    if (data.error) {
        $("#newdir_error").text('Error: ' + data.error);
    } else {
        $("#dialog_newdir").dialog('close');
        sendRequest('list_dir', {});
    }
}

function responseChangeDir(data)
{
    if (!data.result) {
        $("#dialog_error").text(data.result);
        $("#dialog_error").dialog('open');
    } else {
        $('title').text('Simple File Manager - ' + data.result);
        currentPath = data.result;
        sendRequest('list_dir', {path: currentPath});
    }
}

function responsePutToBuffer(data)
{
    if (data.result > 0 && data.action != 'remove') {
        $('#button_paste').show();
        $('#buffer_count').text(data.result);
    }
}

function responsePasteFiles(data)
{
    if (data.error) {
        $("#dialog_error").text(data.error);
        $("#dialog_error").dialog('open');
        return
    }

    if (data.result)
    {
        if (data.result > 0) {
            sendRequest('list_dir', {});
        }
        var action;
        switch (data.action) {
            case 'copy':
                action = 'copied';
            case 'cut':
                $('#button_paste').hide();
                action = 'moved';
        }
        console.log('Successfully ' + action + ' ' + data.result + ' files');
    }
    else {
        console.log('No files were copied or moved.');
    }
}

function responseRemoveFiles(data)
{
    if (data.error) {
        $("#dialog_error").text(data.error);
        $("#dialog_error").dialog('open');
        return
    }

    if (data.result > 0) {
        sendRequest('list_dir', {});
        console.log('Successfully removed '+ data.result + ' files');
    } else {
        console.log('Cat\'t copy or move any file');
    }
}

function sendRequest(action, data)
{
    if (ws.readyState == 3) {
        alert('Connection closed');
    } else if (ws.readyState == 1) {
        $('#dialog_wait').dialog('open');
        $('#wait_message').text('Loading');
        data = data || {};
        var request = $.extend({"do": action}, data);
        request = JSON.stringify(request);
        ws.send(request);
    }
}
