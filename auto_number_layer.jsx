#target photoshop
app.bringToFront();

function getSelectedLayerIndices() {
    var r = new ActionReference();
    r.putProperty(charIDToTypeID('Prpr'), stringIDToTypeID('targetLayers'));
    r.putEnumerated(charIDToTypeID('Dcmn'), charIDToTypeID('Ordn'), charIDToTypeID('Trgt'));
    var out = [];
    try {
        var d = executeActionGet(r).getList(stringIDToTypeID('targetLayers'));
        for (var i = 0; i < d.count; i++) out.push(d.getReference(i).getIndex());
    } catch (e) {
        var r2 = new ActionReference();
        r2.putProperty(charIDToTypeID('Prpr'), charIDToTypeID('ItmI'));
        r2.putEnumerated(charIDToTypeID('Lyr '), charIDToTypeID('Ordn'), charIDToTypeID('Trgt'));
        out.push(executeActionGet(r2).getInteger(charIDToTypeID('ItmI')));
    }
    return out.sort(function(a,b){return a-b;});
}

function selectLayerByIndex(idx, add) {
    var ref = new ActionReference();
    ref.putIndex(charIDToTypeID('Lyr '), idx);
    var desc = new ActionDescriptor();
    desc.putReference(charIDToTypeID('null'), ref);
    if (add) desc.putEnumerated(stringIDToTypeID('selectionModifier'), stringIDToTypeID('selectionModifierType'), stringIDToTypeID('addToSelection'));
    desc.putBoolean(charIDToTypeID('MkVs'), false);
    executeAction(charIDToTypeID('slct'), desc, DialogModes.NO);
}

var base = prompt("Nhập tên gốc (ví dụ: anh):", "anh");
if (base && app.documents.length) {
    var idxs = getSelectedLayerIndices();
    if (!idxs.length) alert("Hãy chọn ít nhất 1 layer.");
    for (var i = 0; i < idxs.length; i++) {
        selectLayerByIndex(idxs[i], false);
        app.activeDocument.activeLayer.name = base + "_" + (i + 1);
    }
    if (idxs.length > 1) {
        selectLayerByIndex(idxs[0], false);
        for (var j = 1; j < idxs.length; j++) selectLayerByIndex(idxs[j], true);
    }
    alert("Đã đổi tên " + idxs.length + " layer.");
}
