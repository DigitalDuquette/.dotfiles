# Linux Remote

When remoting into a remote linux box there are a few QOL features I've come to expect.

This config location serves as a "go-bag" for remote systems.

## COLOR LS

Copy the shell config file to the remote box. You can do this however makes sense:

```sh
scp ~/.config/linux-remote/bootstrap_colorls.sh jjduqu@remote:/tmp/
ssh jjduqu@remote "bash /tmp/bootstrap_colorls.sh"
```

For windows, I'm usually going to mount (or have it mounted already) to my dev machine where a simple `cp bootstrap_colorls.sh /Volumes/C&\Users/jjduqu/Downloads` or similar.

Then, from an activated WSL instance, provide permissions `chmod +x ...` and execute `./.....`
