/**
 * Init buttons
 */

$(document).ready(function() {

    $('#button_up').click(function() {
        actionChangeDir({'path': '', 'name': '..'});
    });

    $('#button_newfile').click(function(){
        $("#dialog_newfile").dialog('open');
    });

    $('#button_newdir').click(function(){
        $("#dialog_newdir").dialog('open');
    });

    $('#button_cut').click(function(){
        actionPutToBuffer('cut');
    });

    $('#button_copy').click(function(){
        actionPutToBuffer('copy');
    });

    $('#button_paste').click(function(){
        $('#dialog_wait').dialog('open');
        $('#wait_message').text('Pasting files');
        sendRequest('paste_files');
    });

    $('#button_delete').click(function(){
        actionRemoveFiles();
    });

    $('#button_properties').click(function(){
        actionShowProperties();
    });

    $('#button_upload').click(function(){
        actionUploadFile();
    });

    $('#button_refresh').click(function(){
        sendRequest('list_dir', {});
    });

    $('#button_orderByName').click(function(){
        actionApplyOrder('name');
    });

    $('#button_orderBySize').click(function(){
        actionApplyOrder('size');
    });

    console.log("This is Simple File Manager default message in your browser console");
});
