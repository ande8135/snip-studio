.class public Lcom/snipstudio/editor/BackCb;
.super Ljava/lang/Object;
.implements Landroid/webkit/ValueCallback;

.field private act:Lcom/snipstudio/editor/MainActivity;

.method public constructor <init>(Lcom/snipstudio/editor/MainActivity;)V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/snipstudio/editor/BackCb;->act:Lcom/snipstudio/editor/MainActivity;
    return-void
.end method

.method public onReceiveValue(Ljava/lang/Object;)V
    .registers 4
    const-string v0, "true"
    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-nez v0, :done
    iget-object v0, p0, Lcom/snipstudio/editor/BackCb;->act:Lcom/snipstudio/editor/MainActivity;
    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Lcom/snipstudio/editor/MainActivity;->moveTaskToBack(Z)Z
    :done
    return-void
.end method
