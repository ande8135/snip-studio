.class public Lcom/snipstudio/editor/MainActivity;
.super Landroid/app/Activity;

.field public web:Landroid/webkit/WebView;
.field public fileCb:Landroid/webkit/ValueCallback;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .registers 6
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
    new-instance v0, Landroid/webkit/WebView;
    invoke-direct {v0, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v0, p0, Lcom/snipstudio/editor/MainActivity;->web:Landroid/webkit/WebView;
    const/4 v2, 0x0
    invoke-virtual {v0, v2}, Landroid/webkit/WebView;->setBackgroundColor(I)V
    invoke-virtual {v0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v1
    const/4 v2, 0x1
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setAllowFileAccess(Z)V
    new-instance v1, Lcom/snipstudio/editor/Chrome;
    invoke-direct {v1, p0}, Lcom/snipstudio/editor/Chrome;-><init>(Lcom/snipstudio/editor/MainActivity;)V
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->setWebChromeClient(Landroid/webkit/WebChromeClient;)V
    new-instance v1, Lcom/snipstudio/editor/Bridge;
    invoke-direct {v1, p0}, Lcom/snipstudio/editor/Bridge;-><init>(Lcom/snipstudio/editor/MainActivity;)V
    const-string v3, "AndroidBridge"
    invoke-virtual {v0, v1, v3}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V
    invoke-virtual {p0, v0}, Lcom/snipstudio/editor/MainActivity;->setContentView(Landroid/view/View;)V
    const-string v3, "file:///android_asset/index.html"
    invoke-virtual {v0, v3}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    return-void
.end method

.method protected onActivityResult(IILandroid/content/Intent;)V
    .registers 10
    iget-object v0, p0, Lcom/snipstudio/editor/MainActivity;->fileCb:Landroid/webkit/ValueCallback;
    if-nez v0, :has
    invoke-super {p0, p1, p2, p3}, Landroid/app/Activity;->onActivityResult(IILandroid/content/Intent;)V
    return-void
    :has
    const/4 v1, 0x0
    iput-object v1, p0, Lcom/snipstudio/editor/MainActivity;->fileCb:Landroid/webkit/ValueCallback;
    const/4 v2, -0x1
    if-ne p2, v2, :deliver
    if-eqz p3, :deliver
    invoke-virtual {p3}, Landroid/content/Intent;->getClipData()Landroid/content/ClipData;
    move-result-object v2
    if-eqz v2, :single
    invoke-virtual {v2}, Landroid/content/ClipData;->getItemCount()I
    move-result v3
    new-array v1, v3, [Landroid/net/Uri;
    const/4 v4, 0x0
    :loop
    if-ge v4, v3, :deliver
    invoke-virtual {v2, v4}, Landroid/content/ClipData;->getItemAt(I)Landroid/content/ClipData$Item;
    move-result-object v5
    invoke-virtual {v5}, Landroid/content/ClipData$Item;->getUri()Landroid/net/Uri;
    move-result-object v5
    aput-object v5, v1, v4
    add-int/lit8 v4, v4, 0x1
    goto :loop
    :single
    invoke-static {p2, p3}, Landroid/webkit/WebChromeClient$FileChooserParams;->parseResult(ILandroid/content/Intent;)[Landroid/net/Uri;
    move-result-object v1
    :deliver
    invoke-interface {v0, v1}, Landroid/webkit/ValueCallback;->onReceiveValue(Ljava/lang/Object;)V
    return-void
.end method

.method public onBackPressed()V
    .registers 4
    iget-object v0, p0, Lcom/snipstudio/editor/MainActivity;->web:Landroid/webkit/WebView;
    const-string v1, "!!(window.androidBack&&window.androidBack())"
    new-instance v2, Lcom/snipstudio/editor/BackCb;
    invoke-direct {v2, p0}, Lcom/snipstudio/editor/BackCb;-><init>(Lcom/snipstudio/editor/MainActivity;)V
    invoke-virtual {v0, v1, v2}, Landroid/webkit/WebView;->evaluateJavascript(Ljava/lang/String;Landroid/webkit/ValueCallback;)V
    return-void
.end method
