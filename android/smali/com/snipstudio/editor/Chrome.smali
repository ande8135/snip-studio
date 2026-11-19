.class public Lcom/snipstudio/editor/Chrome;
.super Landroid/webkit/WebChromeClient;

.field private act:Lcom/snipstudio/editor/MainActivity;

.method public constructor <init>(Lcom/snipstudio/editor/MainActivity;)V
    .registers 2
    invoke-direct {p0}, Landroid/webkit/WebChromeClient;-><init>()V
    iput-object p1, p0, Lcom/snipstudio/editor/Chrome;->act:Lcom/snipstudio/editor/MainActivity;
    return-void
.end method

.method public onShowFileChooser(Landroid/webkit/WebView;Landroid/webkit/ValueCallback;Landroid/webkit/WebChromeClient$FileChooserParams;)Z
    .registers 9
    iget-object v0, p0, Lcom/snipstudio/editor/Chrome;->act:Lcom/snipstudio/editor/MainActivity;
    iget-object v1, v0, Lcom/snipstudio/editor/MainActivity;->fileCb:Landroid/webkit/ValueCallback;
    if-eqz v1, :nocb
    const/4 v2, 0x0
    invoke-interface {v1, v2}, Landroid/webkit/ValueCallback;->onReceiveValue(Ljava/lang/Object;)V
    :nocb
    iput-object p2, v0, Lcom/snipstudio/editor/MainActivity;->fileCb:Landroid/webkit/ValueCallback;
    :try_start
    invoke-virtual {p3}, Landroid/webkit/WebChromeClient$FileChooserParams;->createIntent()Landroid/content/Intent;
    move-result-object v1
    invoke-virtual {p3}, Landroid/webkit/WebChromeClient$FileChooserParams;->getMode()I
    move-result v2
    const/4 v3, 0x1
    if-ne v2, v3, :single
    const-string v4, "android.intent.extra.ALLOW_MULTIPLE"
    invoke-virtual {v1, v4, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Z)Landroid/content/Intent;
    :single
    invoke-virtual {v0, v1, v3}, Lcom/snipstudio/editor/MainActivity;->startActivityForResult(Landroid/content/Intent;I)V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :err
    const/4 v1, 0x1
    return v1
    :err
    const/4 v1, 0x0
    iput-object v1, v0, Lcom/snipstudio/editor/MainActivity;->fileCb:Landroid/webkit/ValueCallback;
    return v1
.end method
