import * as THREE from 'three';
import earcut from 'earcut';

const THRESHOLD = 0.0001;

export function triangulatedSurfacefromVertlist(vertList: number[][], holes: number[] | null = null): THREE.BufferGeometry {
    const unitZ = new THREE.Vector3(0, 0, 1);

    // Calculate normal vector
    let surf_normvec = new THREE.Vector3();
    const vert1 = new THREE.Vector3(...vertList[0]);
    const vert2 = new THREE.Vector3(...vertList[1]);
    const vec1 = new THREE.Vector3().subVectors(vert2, vert1);

    for (let i = 2; i < vertList.length; i++) {
        const vert3 = new THREE.Vector3(...vertList[i]);
        const vec2 = new THREE.Vector3().subVectors(vert3, vert1);
        surf_normvec = new THREE.Vector3().crossVectors(vec1, vec2); // Note: standard cross product order for CCW
        if (surf_normvec.length() > THRESHOLD) {
            break;
        }
    }

    surf_normvec.normalize();
    let triangles: number[] = [];

    if (new THREE.Vector3().crossVectors(surf_normvec, unitZ).length() < THRESHOLD) {
        // Already horizontal
        triangles = earcut(vertList.flat(), holes ?? undefined, 3);
    } else {
        // Rotate to horizontal
        const rotAxis = new THREE.Vector3().crossVectors(surf_normvec, unitZ).normalize();
        const rotAngle = surf_normvec.angleTo(unitZ);
        const rotMatrix = new THREE.Matrix4().makeRotationAxis(rotAxis, rotAngle);

        const vertListRotated = vertList.map(v => {
            const vec = new THREE.Vector3(...v);
            vec.applyMatrix4(rotMatrix);
            return [vec.x, vec.y, vec.z];
        });

        triangles = earcut(vertListRotated.flat(), holes ?? undefined, 3);
    }

    const vertSurf = new Float32Array(triangles.length * 3);
    for (let i = 0; i < triangles.length; i++) {
        const idx = triangles[i];
        vertSurf[i * 3] = vertList[idx][0];
        vertSurf[i * 3 + 1] = vertList[idx][1];
        vertSurf[i * 3 + 2] = vertList[idx][2];
    }

    const surfGeom = new THREE.BufferGeometry();
    surfGeom.setAttribute('position', new THREE.BufferAttribute(vertSurf, 3));
    surfGeom.computeVertexNormals();

    return surfGeom;
}
