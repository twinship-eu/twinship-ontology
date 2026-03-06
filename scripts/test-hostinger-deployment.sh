# This scripts test the last step of the deployment workflow by performing the same rsync operation.
# This will delete the existing files hosted on the ontology website.
#
mkdir -p ~/.ssh
echo "$SSH_KEY" > ~/.ssh/hostinger_deploy_key
chmod 600 ~/.ssh/hostinger_deploy_key

rsync -azP --delete \
  -e "ssh -p $SSH_PORT -i ~/.ssh/hostinger_deploy_key -o StrictHostKeyChecking=no" \
  ./docs/website/documentation/ \
  "$SSH_USER@$SSH_HOST:$DEPLOY_PATH"