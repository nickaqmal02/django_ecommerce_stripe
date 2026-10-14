## how to create ssh key
```bash
ssh-keygen -t ed25519 -C "nikabdulaqmal@gmail.com"
# and then it will generate the ssh key
# it will ask ok what is the key file name 

# ok then you need to read the key file
cat AllKey.pub

# copy those key into the ssh key in github settings

# check if it denied or not
ssh -T git@github.com

# if denied we need to 
eval "$(ssh-agent -s)"

# then we add the key 
ssh-add AllKey

# then review again
ssh -T git@github.com

# finish

# why ed25519
- for speed
- standard

```

