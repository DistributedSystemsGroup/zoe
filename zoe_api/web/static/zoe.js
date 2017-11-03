function format_bytes(bytes, decimals) {
    if(bytes === 0) {
        document.write('0 Byte');
        return;
    }
    var k = 1024;
    var dm = decimals + 1 || 3;
    var sizes = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    document.write((bytes / Math.pow(k, i)).toPrecision(dm) + ' ' + sizes[i]);
}

function format_bytes_ret(bytes, decimals) {
    if(bytes === 0) {
        return '0 Byte';
    }
    var k = 1024;
    var dm = decimals + 1 || 3;
    var sizes = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toPrecision(dm) + ' ' + sizes[i];
}
