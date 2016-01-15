#!/bin/bash

pushd ../utils
. base.sh
popd

for id in `cat state.zoe`; do
	echo -n "Deleting container "
	$DOCKER rm -f $id
done

rm state.zoe

